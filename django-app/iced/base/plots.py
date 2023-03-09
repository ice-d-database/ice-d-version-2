from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.layouts import column
from bokeh.embed import components
from numpy import array, where, unique, append, linspace, sqrt, power, exp, argsort
from numpy.random import default_rng

from math import floor, ceil, pi

def nuclide_colors():
    # This is just here so that you can define the colors associated with each nuclide only once.
    nucs = ['He-3 (qtz)', 'He-3 (px)', 'He-3 (ol)', 'Be-10 (qtz)', 'C-14 (qtz)', 'Ne-21 (qtz)', 'Al-26 (qtz)', 'Cl-36']
    fcols = ['#C7C7C7', '#999999', '#999999', '#F74A4A', '#FFA826', '#EFFF40', '#4090E6', '#9A56A6', ]
    lcols = ['#474747', '#1A1A1A', '#1A1A1A', '#782424', '#805413', '#788020', '#1D4066', '#231426', ]

    return nucs, fcols, lcols


def age_elevation_plot(v3_age_results,cl36_age_results,sample_dict):
    # The reason this is so long is that it has to unpack the exposure age results (which
    # contains sample names and exposure ages, but there can be multiple exposure ages per
    # sample) and match them up with other sample-related info (i.e., what the sample is,
    # associated ice surface elevations, etc.)

    # unpack dict of sample related info generated upstream
    sample_names = sample_dict["names"]
    sample_whats = sample_dict["whats"]
    sample_elvs = sample_dict["elvs"]

    # initialize arrays of unknown size - separate arrays for bedrock and non-bedrock
    plot_t_br = []
    plot_dti_br = []
    plot_dte_br = []
    plot_elv_br = []
    plot_fcol_br = []
    plot_lcol_br = []
    plot_name_br = []
    plot_nuc_br = []
    plot_what_br = []
    # Non-bedrock
    plot_t = []
    plot_dti = []
    plot_dte = []
    plot_elv = []
    plot_fcol = []
    plot_lcol = []
    plot_name = []
    plot_nuc = []
    plot_what = []

    # get colors

    [nucs,fcols,lcols] = nuclide_colors()

    # Note: this shouldn't be called if there are no exposure-age results.
    # Loop through age results and assign ages with matching sample info to
    # bedrock or non-bedrock arrays.

    if v3_age_results:
        for this_name in v3_age_results.keys():
            this_sample = v3_age_results[this_name]["LSD"]
            for nname in this_sample:
                this_nuclide = this_sample[nname]
                for age in this_nuclide:
                    if age[0] != '0':
                        # This appends to separate list for bedrock and non-bedrock samples.
                        if 'edrock' in sample_whats[sample_names.index(this_name)]:
                            plot_t_br.append(int(age[0]))
                            plot_dti_br.append(int(age[1]))
                            plot_dte_br.append(int(age[2]))
                            plot_fcol_br.append(fcols[nucs.index(nname)])
                            plot_lcol_br.append(lcols[nucs.index(nname)])
                            plot_elv_br.append(sample_elvs[sample_names.index(this_name)])
                            plot_name_br.append(this_name)
                            plot_nuc_br.append(nname)
                            plot_what_br.append(sample_whats[sample_names.index(this_name)])
                        else:
                            plot_t.append(int(age[0]))
                            plot_dti.append(int(age[1]))
                            plot_dte.append(int(age[2]))
                            plot_fcol.append(fcols[nucs.index(nname)])
                            plot_lcol.append(lcols[nucs.index(nname)])
                            plot_elv.append(sample_elvs[sample_names.index(this_name)])
                            plot_name.append(this_name)
                            plot_nuc.append(nname)
                            plot_what.append(sample_whats[sample_names.index(this_name)])

    # Do the same thing for Cl-36 if present. Append to same arrays.
    # Note: added problem here is that the Cl-36 calculator input has had an aliquot
    # name added to the sample name, so the original sample name won't match the sample
    # name in the results.

    if cl36_age_results:
        for this_name in cl36_age_results.keys():
            this_sample = cl36_age_results[this_name]["LSD"]
            # Now this_name is a sample name with aliquot. We need to match it to a sample
            # name without aliquot, which is in the sample_names list.
            nmatchi = int(where([tryn in this_name for tryn in sample_names])[0][0])

            for nname in this_sample:
                this_nuclide = this_sample[nname]
                for age in this_nuclide:
                    if age[0] != '0':
                        # Appends to existing lists.
                        if 'edrock' in sample_whats[nmatchi]:
                            plot_t_br.append(int(age[0]))
                            plot_dti_br.append(int(age[1]))
                            plot_dte_br.append(int(age[1])) # This is a hack because Cl-36 external error is unreliable and sometimes returns NaN
                            plot_fcol_br.append(fcols[nucs.index(nname)])
                            plot_lcol_br.append(lcols[nucs.index(nname)])
                            plot_elv_br.append(sample_elvs[nmatchi])
                            plot_name_br.append(this_name)
                            plot_nuc_br.append(nname)
                            plot_what_br.append(sample_whats[nmatchi])
                        else:
                            plot_t.append(int(age[0]))
                            plot_dti.append(int(age[1]))
                            plot_dte.append(int(age[1])) # likewise
                            plot_fcol.append(fcols[nucs.index(nname)])
                            plot_lcol.append(lcols[nucs.index(nname)])
                            plot_elv.append(sample_elvs[nmatchi])
                            plot_name.append(this_name)
                            plot_nuc.append(nname)
                            plot_what.append(sample_whats[nmatchi])

    # Get elevation limits
    z_low = floor(min(plot_elv + plot_elv_br) / 100.0 ) * 100.0 - 25
    z_hi = ceil(max(plot_elv + plot_elv_br) / 100.0) * 100.0 + 25

    if z_low == z_hi:
        z_low = z_low - 100
        z_hi = z_hi + 100


    # Jitter the elevation data a bit so error bars don't overplot
    jitter_size = (z_low-z_hi) * 0.03
    rng = default_rng()
    plot_elv_jittered = array(plot_elv) + ( rng.random(len(plot_elv)) * jitter_size ) - ( jitter_size / 2.0 )
    plot_elv_br_jittered = array(plot_elv_br) + ( rng.random(len(plot_elv_br)) * jitter_size ) - ( jitter_size / 2.0 )

    # create data dicts
    data = {'x': array(plot_t),
            'xmax1': array(plot_t) + array(plot_dti),
            'xmin1': array(plot_t) - array(plot_dti),
            'xmax2': array(plot_t) + array(plot_dte),
            'xmin2': array(plot_t) - array(plot_dte),
            'y': plot_elv_jittered,
            'plot_fcol': array(plot_fcol),
            'plot_lcol': array(plot_lcol),
            'name': array(plot_name),
            'what': array(plot_what),
            'nuc': array(plot_nuc)}

    data_br = {'x': array(plot_t_br),
               'xmax1': array(plot_t_br) + array(plot_dti_br),
               'xmin1': array(plot_t_br) - array(plot_dti_br),
               'xmax2': array(plot_t_br) + array(plot_dte_br),
               'xmin2': array(plot_t_br) - array(plot_dte_br),
               'y': plot_elv_br_jittered,
               'plot_fcol': array(plot_fcol_br),
               'plot_lcol': array(plot_lcol_br),
               'name': array(plot_name_br),
               'what': array(plot_what_br),
               'nuc': array(plot_nuc_br)}

    # Define what is in popups
    TOOLTIPS = """
    <div>
        <span style="font-size: 14px;">@name - @what - @nuc - @x yr</span>
    </div>
    """

    # This is kind of stupid because it has to deal with either one being empty.

    maxx = max( list(data['xmax2']) + list(data_br['xmax2']) )


    # Create main figure
    p = figure(
        tools='',
        tooltips=TOOLTIPS,
        height=450,
        width=600,
        x_range=(1, (maxx * 1.1)),
        background_fill_color="darkslategray",
        background_fill_alpha=0.3,
        border_fill_color="#EEEEEE"
    )
    # styling
    p.yaxis.major_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.yaxis.major_label_text_font = "Arial"
    p.xaxis.major_label_text_font = "Arial"
    p.yaxis.major_label_text_font_size = "10pt"
    p.xaxis.major_label_text_font_size = "10pt"
    p.xaxis.axis_label = "Exposure age (yr)"
    p.xaxis.axis_label_text_font = "Arial"
    p.xaxis.axis_label_text_font_size = "10pt"
    p.xaxis.axis_label_text_align = "left"
    p.yaxis.axis_label_text_align = "left"
    p.yaxis.axis_label = "Elevation (m)"
    p.yaxis.axis_label_text_font = "Arial"
    p.yaxis.axis_label_text_font_size = "10pt"
    p.yaxis.axis_line_color = None

    if len(plot_t) > 0:
        # Plot error bars for erratics
        p.hbar(y='y', left='xmin1', right='xmax1', source=data, height=0, line_width=1, line_color='plot_lcol',
           fill_color=None)

    if len(plot_t_br) > 0:
        # Plot error bars for bedrock
        p.hbar(y='y', left='xmin1', right='xmax1', source=data_br, height=0, line_width=1, line_color='plot_lcol',
           fill_color=None)

    if len(plot_t) > 0:
        # Plot erratics
        p.circle(x='x', y='y', size=11, source=data, line_color='plot_lcol', fill_color='plot_fcol', line_width=1)

    if len(plot_t_br) > 0:
        # Plot bedrock
        p.square(x='x', y='y', size=11, source=data_br, line_color='plot_lcol', fill_color='plot_fcol', line_width=1)

    # Plot ice surface elevations
    ice_elvs = unique(array([x for x in sample_dict["ice"] if x is not None]))
    if any(ice_elvs):
        data_ice = {'y': ice_elvs,
                    'xmin': ice_elvs - ice_elvs,
                    'xmax': ice_elvs - ice_elvs + 20e6}
        p.hbar(y='y', left='xmin', right='xmax', source=data_ice, line_width=0.5, line_color='steelblue', line_dash="dashed", fill_color=None)
        if min(ice_elvs) < (z_low + 25):
            z_low = min(ice_elvs) - 25

    # bounds sets the absolute zoom/pan limit
    p.x_range.bounds = (0, (maxx * 1.1))
    p.y_range.bounds = (z_low, z_hi)
    # then this sets the initial range
    p.y_range.start = z_low
    p.y_range.end = z_hi

    # Second axes for drag tool
    p2 = figure(
        height=110,
        width=600,
        y_range=p.y_range,
        y_axis_type=None,
        x_axis_type='log',
        tools="",
        toolbar_location=None,
        background_fill_color="whitesmoke",
        x_range=(100, 20e6),
        x_axis_location="above",
        border_fill_color="#EEEEEE"
    )

    # styling
    p2.xgrid.grid_line_color = "grey"
    p2.xgrid.minor_grid_line_color = "lightgrey"
    p2.x_range.bounds = p.x_range.bounds
    p2.xaxis.axis_label = ""
    p2.xaxis.axis_label_text_align = 'left'
    p2.xaxis.axis_label_text_font = 'Arial'
    p2.xaxis.axis_label_text_font_size = '10pt'
    p2.ygrid.grid_line_color = None

    # range tool and link to other axes
    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "darkslategray"
    range_tool.overlay.fill_alpha = 0.3
    p2.add_tools(range_tool)
    p2.toolbar.active_multi = range_tool

    # plot data on index plot too
    p2.circle('x', 'y', source=data, color="darkslategray")
    p2.square('x', 'y', source=data_br, color="darkslategray")

    return components(column(p2, p))


def camelplot(v3_age_results,cl36_age_results,sample_dict):
    # Note: this is a lot of lines of code to do something that is not that complicated.
    # Could be improved.
    # unpack dict of sample related info generated upstream
    sample_names = sample_dict["names"]
    sample_whats = sample_dict["whats"]

    # initialize arrays of unknown size
    plot_t = array([])
    plot_dti = plot_t
    plot_dte = plot_t
    plot_fcol = plot_t
    plot_lcol = plot_t
    plot_name = plot_t
    plot_nuc = plot_t
    plot_what = plot_t

    [nucs, fcols, lcols] = nuclide_colors()

    # Loop through age results and assign ages with matching sample info to
    # bedrock or non-bedrock arrays.

    sample_max = []
    sorting_names = []

    if v3_age_results:
        for this_name in v3_age_results.keys():
            this_sample = v3_age_results[this_name]["LSD"]
            sample_ages = []
            isdata_this_sample = False
            for nname in this_sample:
                this_nuclide = this_sample[nname]
                for age in this_nuclide:
                    if age[0] != '0':
                        isdata_this_sample = True
                        # Append to lists
                        plot_t = append(plot_t,int(age[0]))
                        plot_dti = append(plot_dti,int(age[1]))
                        plot_dte = append(plot_dte,int(age[2]))
                        plot_fcol = append(plot_fcol, fcols[nucs.index(nname)])
                        plot_lcol = append(plot_lcol, lcols[nucs.index(nname)])
                        plot_name = append(plot_name,this_name)
                        plot_nuc = append(plot_nuc,nname)
                        plot_what = append(plot_what,sample_whats[sample_names.index(this_name)])
                        sample_ages.append(int(age[0]))

            if isdata_this_sample:
                sample_max.append(max(sample_ages))
                sorting_names.append(this_name)

    if cl36_age_results:
        for this_name in cl36_age_results.keys():
            this_sample = cl36_age_results[this_name]["LSD"]
            # Now this_name is a sample name with aliquot. We need to match it to a sample
            # name without aliquot, which is in the sample_names list.
            nmatchi = int(where([tryn in this_name for tryn in sample_names])[0][0])
            sample_ages = []
            isdata_this_sample = False
            for nname in this_sample:
                this_nuclide = this_sample[nname]
                for age in this_nuclide:
                    if age[0] != '0':
                        isdata_this_sample = True
                        # Appends to existing lists.
                        plot_t = append(plot_t, int(age[0]))
                        plot_dti = append(plot_dti, int(age[1]))
                        plot_dte = append(plot_dte, int(age[1])) # hack b/c exterr is unreliable for Cl-36, sometimes returns NaN
                        plot_fcol = append(plot_fcol, fcols[nucs.index(nname)])
                        plot_lcol = append(plot_lcol, lcols[nucs.index(nname)])
                        plot_name = append(plot_name, this_name)
                        plot_nuc = append(plot_nuc, nname)
                        plot_what = append(plot_what, sample_whats[nmatchi])
                        sample_ages.append(int(age[0]))

            if isdata_this_sample:
                sample_max.append(max(sample_ages))
                sorting_names.append(this_name)

    # Now generate camelplots
    # Find bounds
    minx = min(plot_t - 3*plot_dti)
    # Stop at zero
    if minx < 0:
        minx = 0

    maxx = max(plot_t + 3*plot_dti)
    plotx = linspace(minx,maxx,400)

    # Generate Gaussian kernels on plot_x for all data
    all_camels = []
    for a in range(0,len(plot_t)):
        # Normal distribution
        this_camel = exp(-0.5 * power(((plotx - plot_t[a])/plot_dti[a]),2)) / (sqrt(2 * pi) * plot_dti[a])
        all_camels.append(this_camel)

    # Summary camel plot for all nuclides, except He-3/qtz
    cplot_all = plotx - plotx  # zeros
    for a in range(0,len(plot_t)):
        # Leave out He-3 in quartz
        if plot_nuc[a] != 'He-3 (qtz)':
            cplot_all = cplot_all + all_camels[a]

    # The below is to suppress weird normalizations if individual plots are spiky.
    nf = [max(cplot_all)]

    p = figure(height=150,
               width=800,
               x_range=[0,maxx*1.1],
               x_axis_type=None,
               y_axis_type=None,
               toolbar_location=None,
               title="LSDn",
               border_fill_color="#EEEEEE",
               background_fill_color = "#EEEEEE"
               )

    p.title.text_font_size='14pt'
    p.outline_line_color = None

    # If there are multiple nuclides, make nuclide-specific camel plots.
    unique_nuclides = set(plot_nuc)
    if len(unique_nuclides) > 1:
        nuclide_camels = []
        # Case we have multiple nuclides. Make multiple camel plots.
        offset = 0
        for this_nuclide in unique_nuclides:
            offset = offset - 0.05
            indices = where(this_nuclide == plot_nuc)
            this_camel = plotx - plotx
            for a in indices[0]:
                this_camel = this_camel + all_camels[a]
                this_nf = max([nf, max(this_camel)])
            p.line(x=plotx,y=(this_camel / this_nf + offset),line_color=fcols[nucs.index(this_nuclide)],line_width=1)

    # Now plot the one for all nuclides on top
    # This actually has to be conditional to cover the case where there are only He-3-in-qtz data, in which case
    # we don't want to just plot zeros.
    if max(cplot_all) > 0:
        p.line(x=plotx,y=(cplot_all / nf ),line_color='black',line_width=2)

    # Now plot additional axes with dots and bars
    TOOLTIPS = """
        <div>
            <span style="font-size: 14px;">@name - @what - @nuc - @x yr</span>
        </div>
        """

    # What we are trying to do here is keep multiple measurements for one sample on the same line,
    # but sort them by the oldest age for each sample. The result is that this is super clunky, it seems
    # like there should be a better algorithm for this.

    sample_max = array(sample_max)
    sorting_names = array(sorting_names)
    sample_sort_i = argsort(sample_max)
    sorted_names = sorting_names[sample_sort_i]

    y = plot_t - plot_t # zeros
    a = 1
    for n1 in sorted_names:
        b = 0
        for n2 in plot_name:
            if n1 == n2:
                y[b] = a

            b = b + 1

        a = a + 1

    # OK, now ready to plot
    p2data = {'x': plot_t,
            'y': y,
            'xmin': plot_t - plot_dti,
            'xmax': plot_t + plot_dti,
            'plot_fcol': array(plot_fcol),
            'plot_lcol': array(plot_lcol),
            'name': plot_name,
            'what': plot_what,
            'nuc': plot_nuc}

    p2 = figure(height= 30 + 10*(len(sorted_names) + 4),
                width=800,
                x_range=[0,maxx*1.1],
                y_range=[-3,(len(sorted_names)+2)],
                y_axis_type=None,
                toolbar_location=None,
                x_axis_label="Exposure age (yr)",
                tooltips=TOOLTIPS,
                border_fill_color="#EEEEEE",
                background_fill_color="#EEEEEE"
                )

    p2.hbar(y='y',left='xmin',right='xmax',source=p2data,height=0,fill_color=None,line_color='plot_lcol')
    p2.circle(y='y',x='x',fill_color='plot_fcol',line_color='plot_lcol',source=p2data,size=10)
    p2.outline_line_color = None
    p2.xgrid.visible=False

    [plot_script, plot_div] = components(column(p, p2))

    # Add some explanatory text if necessary
    if 'He-3 (qtz)' in unique_nuclides:
        plot_div = plot_div + "<div><p>Note: He-3-in-quartz data are not included in the summary KDE.</p></div>"

    return plot_script,plot_div

def NofZplot(depth_nuclide_data):
    # This plots downcore nuclide concentrations.

    [nucs, fcols, lcols] = nuclide_colors()

    # Fill arrays with data
    td = array([])
    bd = array([])
    N = array([])
    dN = array([])
    lcol = array([])
    fcol = array([])
    nid = array([])

    # This matches up nuclides to stuff that is in the input arg dict

    nnames = {'He-3 (qtz)': 'n3_atoms_g',
              'He-3 (px/ol)': 'n3_atoms_g',
              'Be-10 (qtz)': 'n10_atoms_g',
              'C-14 (qtz)': 'n14_atoms_g',
              'Ne-21 (qtz)': 'n21_atoms_g',
              'Al-26 (qtz)': 'n26_atoms_g'}
    dnnames = {'He-3 (qtz)': 'deln3_atoms_g',
              'He-3 (px/ol)': 'deln3_atoms_g',
               'Be-10 (qtz)': 'deln10_atoms_g',
               'C-14 (qtz)': 'deln14_atoms_g',
               'Ne-21 (qtz)': 'deln21_atoms_g',
               'Al-26 (qtz)': 'deln26_atoms_g'}

    # Read data out into arrays for plotting
    for k in depth_nuclide_data.keys():
        this_nuclide = k
        this_fcol = fcols[nucs.index(this_nuclide)]
        this_lcol = lcols[nucs.index(this_nuclide)]
        this_data = depth_nuclide_data[k]
        this_nname = nnames[k]
        this_dnname = dnnames[k]
        if this_data is not None:
            for this_item in this_data:
                td = append(td, int(this_item['top_depth_cm']))
                bd = append(bd, int(this_item['bot_depth_cm']))
                fcol = append(fcol, this_fcol)
                lcol = append(lcol, this_lcol)
                N = append(N, int(this_item[this_nname]))
                dN = append(dN, this_item[this_dnname])
                nid = append(nid, this_nuclide)

    if len(N) > 0:

        maxz = max(bd) * 1.05
        fht = min(800,round(max(350, maxz * 0.8)))

        TOOLTIPS = """
                <div>
                    <span style="font-size: 14px;">@nid: @td-@bd cm</span>
                </div>
                """

        data = {'y': ((td + bd) / 2),
                'height': (bd - td),
                'left': (N - dN),
                'right': (N + dN),
                'fill_color': fcol,
                'line_color': lcol,
                'nid': nid,
                'td': td,
                'bd': bd
                }

        # Create main figure
        p = figure(
            tools='',
            height=fht,
            width=500,
            background_fill_color='#EEEEEE',
            border_fill_color="#EEEEEE",
            x_axis_type='log',
            y_range=(maxz, 0),
            tooltips=TOOLTIPS,
        )

        # bounds sets the absolute zoom/pan limit
        p.y_range.bounds = (0, maxz)

        p.xaxis.axis_label = "Nuclide concentration (atoms/g)"
        p.xaxis.axis_label_text_font = 'Arial'
        p.xaxis.axis_label_text_font_size = '10pt'
        p.yaxis.axis_label = "Depth (cm)"
        p.yaxis.axis_label_text_font = 'Arial'
        p.yaxis.axis_label_text_font_size = '10pt'

        p.hbar(y='y',
               height='height',
               left='left',
               right='right',
               fill_color='fill_color',
               line_color='line_color',
               source=data,
               fill_alpha=0.5,
               line_width=0.5,
               line_alpha=0.5
               )

        p.vbar(x=N,
               top=td,
               bottom=bd,
               width=0,
               line_color=lcol,
               line_width=0.75
               )

        # return plot html components
        [plot_script, plot_div] = components(p)
    else:
        # return empty strings
        plot_script = ''
        plot_div = ''

    return plot_script, plot_div